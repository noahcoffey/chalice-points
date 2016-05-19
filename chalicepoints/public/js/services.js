(function() {
  'use strict';
  angular.module('chalicepoints.services', [
    'ngResource',
    'chalicepoints.filters'
  ])
  .constant('Types', {
    'peer': 'Approach everyone as a peer, regardless of title',
    'agile': 'Be agile and iterate',
    'communication': 'Communicate Status',
    'transparency': 'Default to transparency with each other',
    'problemsolving': 'Get to work on solving problems',
    'helpothers': 'Help others succeed',
    'positivity': 'Inject positivity into all of your interactions',
    'results': 'Results matter',
    'growth': 'Seek growth',
    'other': 'High Five'
  })
  .constant('TypeOrder', [
    'peer',
    'agile',
    'communication',
    'transparency',
    'problemsolving',
    'helpothers',
    'positivity',
    'results',
    'growth',
    'other'
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
  .factory('History', function($resource) {
    var History = $resource('/api/1.0/history/:type', {
      type: '@type'
    },{
      query: {
        method: 'POST'
      }
    });

    History.load = function(type, params) {
      var query = $.extend({'type': type}, params['common'], params[type])
      return History.query(query).$promise;
    };

    return History;
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
