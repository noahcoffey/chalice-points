(function() {
 'use strict';
  angular.module('chalicepoints.filters', [])
  .filter('dateMoment', function($filter) {
    var dateFilter = $filter('date');
    return function(dateString, format) {
      var momentDate = moment(dateString).toDate();
      return dateFilter(momentDate, format);
    };
  })
  .filter('join', function($filter) {
    return function(arr, delimiter) {
      return arr.join(delimiter);
    };
  })
  .filter('amountMax', function($filter) {
    return function(arr) {
      var maxAmount = 0;
      for (var idx in arr) {
        maxAmount = Math.max(maxAmount, arr[idx].amount);
      }

      return maxAmount;
    };
  });
})();
