# Lambda runs this Dockerfile on the MicroVM base image, starts the server,
# waits for the /ready hook, and snapshots the running MicroVM.
# The Lambda container base image includes a snapshot-safe OpenSSL.
FROM public.ecr.aws/lambda/microvms:al2023-minimal

# glibc-common provides getconf, which SAAF uses to read CLK_TCK.
RUN dnf install -y java-21-amazon-corretto-headless glibc-common && dnf clean all

WORKDIR /app
COPY saaf-microvm.jar .

EXPOSE 8080
CMD ["java", "-jar", "saaf-microvm.jar"]
