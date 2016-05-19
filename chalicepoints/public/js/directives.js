(function() {
  'use strict';
  angular.module('chalicepoints.directives', [])
  .directive('datepicker', ['$parse', function($parse) {
    return {
      restrict: 'A',
      require : 'ngModel',
      link : function ($scope, $element, $attrs, ngModelCtrl) {
        $(function() {
          var handler = $parse($attrs.datepicker);

          $element.datepicker({
            dateFormat: 'yy-mm-dd',
            onSelect: function (date) {
              $scope.$apply(function () {
                ngModelCtrl.$setViewValue(date);
                handler();
              });
            }
          });
        });
      }
    }
  }]);
})();
