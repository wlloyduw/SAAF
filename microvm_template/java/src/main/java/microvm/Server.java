package microvm;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonSyntaxException;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * AWS Lambda MicroVM server.
 *
 * Lambda starts this server while it builds the MicroVM image, snapshots it, and
 * sends requests for each MicroVM to port 8080. Requests to the lifecycle hooks
 * are answered here. Every other request is passed to Hello: fields from the JSON
 * body and query string are copied onto the request, and the SAAF attributes it
 * returns are sent back as JSON.
 *
 * Requests are handled one at a time, so CPU and memory deltas belong to one request.
 *
 * @author Robert Cordingly
 */
public class Server {

    private static final int PORT = 8080;
    private static final String HOOKS = "/aws/lambda-microvms/runtime/v1/";
    private static final Set<String> RESERVED = new HashSet<>(Arrays.asList("method", "path", "query", "headers", "body"));
    private static final Gson GSON = new GsonBuilder().disableHtmlEscaping().create();

    public static void main(String[] args) throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", PORT), 0);
        server.createContext("/", Server::handle);
        server.start();
        System.out.println("SAAF MicroVM server listening on port " + PORT);
    }

    private static void handle(HttpExchange exchange) throws IOException {
        try {
            URI uri = exchange.getRequestURI();
            String path = uri.getPath();
            String text = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);

            // Lambda calls /ready during the image build, before the snapshot, and /run
            // when a MicroVM starts from the snapshot, with that MicroVM's ID.
            if (path.equals(HOOKS + "ready")) {
                sendJson(exchange, 200, new HashMap<>());
                return;
            }
            if (path.equals(HOOKS + "run")) {
                String microvmId = "";
                try {
                    Object id = GSON.fromJson(text, Map.class).get("microvmId");
                    microvmId = id == null ? "" : id.toString();
                } catch (JsonSyntaxException | NullPointerException e) {
                    //Write an empty ID when the body is not a JSON object.
                }
                Files.write(Paths.get("/tmp/microvm-id"), microvmId.getBytes(StandardCharsets.UTF_8));
                sendJson(exchange, 200, new HashMap<>());
                return;
            }

            Object body;
            try {
                body = text.isEmpty() ? new HashMap<>() : GSON.fromJson(text, Object.class);
            } catch (JsonSyntaxException e) {
                sendJson(exchange, 400, error("Request body is not valid JSON"));
                return;
            }

            Map<String, Object> query = parseQuery(uri.getRawQuery());
            Map<String, Object> headers = new LinkedHashMap<>();
            for (Map.Entry<String, List<String>> header : exchange.getRequestHeaders().entrySet()) {
                headers.put(header.getKey().toLowerCase(), String.join(",", header.getValue()));
            }

            HashMap<String, Object> request = new HashMap<>();
            request.put("method", exchange.getRequestMethod());
            request.put("path", path);
            request.put("query", query);
            request.put("headers", headers);
            request.put("body", body);
            if (body instanceof Map) {
                applyFields(request, (Map<?, ?>) body);
            }
            applyFields(request, query);

            try {
                sendJson(exchange, 200, new Hello().handleRequest(request, new HashMap<>()));
            } catch (Exception e) {
                sendJson(exchange, 500, error(e.toString()));
            }
        } finally {
            exchange.close();
        }
    }

    private static void applyFields(Map<String, Object> target, Map<?, ?> source) {
        for (Map.Entry<?, ?> field : source.entrySet()) {
            String key = String.valueOf(field.getKey());
            if (!RESERVED.contains(key) && !target.containsKey(key)) {
                target.put(key, field.getValue());
            }
        }
    }

    private static Map<String, Object> parseQuery(String rawQuery) throws IOException {
        Map<String, Object> query = new LinkedHashMap<>();
        if (rawQuery == null || rawQuery.isEmpty()) {
            return query;
        }
        for (String pair : rawQuery.split("&")) {
            int separator = pair.indexOf('=');
            String key = separator < 0 ? pair : pair.substring(0, separator);
            String value = separator < 0 ? "" : pair.substring(separator + 1);
            query.put(URLDecoder.decode(key, "UTF-8"), URLDecoder.decode(value, "UTF-8"));
        }
        return query;
    }

    private static Map<String, Object> error(String message) {
        Map<String, Object> error = new HashMap<>();
        error.put("error", message);
        return error;
    }

    private static void sendJson(HttpExchange exchange, int statusCode, Object payload) throws IOException {
        byte[] body = GSON.toJson(payload).getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(statusCode, body.length);
        try (OutputStream output = exchange.getResponseBody()) {
            output.write(body);
        }
    }
}
