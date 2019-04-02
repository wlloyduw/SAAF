/**
 * AWS Lambda Default Handler
 *
 * @param event
 */
exports.handler = async (event) => {
    let name = event.name;
    const reg = require('./Register');
    const myReg = new reg();
    let res = myReg.profileVM();
    res['name'] = name;
    res['message'] = 'Hello ' + name + ' from Node JS Lambda!';
    return res;
};


/**
 * Google Cloud Functions Default Handler
 *
 * @param req
 * @param res
 
exports.myHandler = (req, res) => {
    let name = req.name;
    const reg = require('./Register');
    const myReg = new reg();
    let res = myReg.profileVM();
    res['name'] = name;
    res['message'] = 'Hello ' + name + ' from Node JS GCF!';

    res.status(200).send(res);
};

/**
 * IBM Cloud Functions Default Handler
 *
 * @param params
 * @returns {{message: string}}
 
function main(params) {
    let name = params.name;
    const reg = require('./Register');
    const myReg = new reg();
    let res = myReg.profileVM();
    res['name'] = name;
    res['message'] = 'Hello ' + name + ' from Node JS IBM!';
    return res;
}

/**
 * Azure Functions Default Handler
 *
 * @param context
 * @param req
 * @returns {Promise<void>}
 
module.exports = async function (context, req) {

    let name = req.name;
    const reg = require('./Register');
    const myReg = new reg();
    let res = myReg.profileVM();
    res['name'] = name;
    res['message'] = 'Hello ' + name + ' from Node JS Azure!';

    context.res = {
        status: 200,
        body: res
    };
};

/**
*/