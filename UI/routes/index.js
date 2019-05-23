var express = require('express');
var router = express.Router();
var zerorpc = require("zerorpc");

var client = new zerorpc.Client();
client.connect("tcp://127.0.0.1:4242");

router.get('/api/getSuggestion', function(req, res, next) {
  //console.log(req.query)
  client.invoke("predictnextword", req.query, function(error, result, more) {
    //console.log('result : ',result);
    res.status(200).json({'status' : result})
  });

});

/* GET home page. */
router.get('/', function(req, res, next) {
    res.sendfile('./views/index.html');
});

module.exports = router;
