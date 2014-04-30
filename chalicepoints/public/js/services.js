(function() {
  'use strict';
  angular.module('chalicepoints.services', [
    'ngResource',
    'chalicepoints.filters'
  ])
  .factory('Leaderboard', function($resource) {
      return $resource('/api/1.0/leaderboard/:type', {
          type: 'all'
      });
  })
  .factory('User', function($resource) {
      return $resource('/api/1.0/user/:id', {
          id: '@id'
      }, {
        update: {
          method: 'PUT'
        },
        merge: {
          url: '/api/1.0/merge/:id/:targetId',
          method: 'POST',
          params: {
            id: '@id',
            targetId: '@target'
          }
        }
      });
  })
  .factory('Winner', function($resource) {
      return $resource('/api/1.0/winners', {});
  })
  .factory('Timeline', function($resource) {
      return $resource('/api/1.0/timeline', {});
  })
  .factory('CPEvent', function($resource) {
      return $resource('/api/1.0/event/:id', {
          id: "@id"
      }, {
        update: {
          method: 'PUT'
        }
      });
  })
  .factory('flash', function($rootScope, $timeout) {
      $rootScope.message = {};

      var reset;
      var cleanup = function() {
          $timeout.cancel(reset);
          reset = $timeout(function() {
              $('.alert-box').slideUp(400, function() {
                  $rootScope.message = {};
              });
          }, 2000);
      };

      return function(level, text) {
          $rootScope.message = {
              level: level,
              text: text
          };

          $('.alert-box').slideDown();

          cleanup();
      };
  });
})();
