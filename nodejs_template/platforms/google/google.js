/**
 * Google Cloud Functions Default Function
 *
 * @param req
 * @param res
 */
exports.helloWorld = (req, res) => {
	res.status(200).send((require('./function'))(req.body));
};