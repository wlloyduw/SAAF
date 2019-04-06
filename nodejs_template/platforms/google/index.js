/**
 * Google Cloud Functions Default Function
 *
 * This hander is used as a bridge to call the platform neutral
 * version in function.js. This script is put into the scr directory
 * when using publish.sh.
 *
 * @param req
 * @param res
 */
exports.helloWorld = (req, res) => {
	res.status(200).send((require('./function'))(req.body));
};