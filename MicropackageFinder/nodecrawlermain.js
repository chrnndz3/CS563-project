var _ = require('lodash');
const registry = _.shuffle(require('all-the-package-names'))
const fs = require('fs')
const package_names = registry.slice(0,500)
const url = 'https://www.npmjs.com/package/'

try{
  fs.unlinkSync('./package-names.csv');
}catch (err) {
}

// Start creating the file for the helper python program
var logger = fs.createWriteStream('package-names.csv', {flags: 'a' })
for (i = 0; i < package_names.length; i++) {
  logger.write(package_names[i]+', '+url + package_names[i] + '\n')
}