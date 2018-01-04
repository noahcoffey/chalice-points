(function() {
  'use strict';
  angular.module('chalicepoints.services', [
    'ngResource',
    'chalicepoints.filters'
  ])
  .constant('Types', {
    'peer': 'Approach everyone as a peer, regardless of title',
    'agile': 'Be agile and iterate',
    'transparency': 'Default to transparency with each other',
    'problemsolving': 'Get to work on solving problems',
    'helpothers': 'Help others succeed',
    'growth': 'Seek growth',
    'other': 'High Five'
  })
  .constant('GroupOrder', [
      'Results Matter',
      'Relationships Matter',
      'Other'
  ])
  .constant('TypeGroups', {
    'Results Matter': [
      'agile',
      'problemsolving',
      'growth'
    ],
    'Relationships Matter': [
      'peer',
      'transparency',
      'helpothers'
    ],
    'Other': [
      'other'
    ]
  })
  .factory('Leaderboard', function($resource) {
    return $resource('/api/1.0/leaderboard/:type', {
      type: 'all'
    });
  })
  .factory('User', function($resource) {
    return $resource('/api/1.0/user/:id/:action', {
      id: '@id'
    }, {
      targets: {
        method: 'GET',
        params: {
          id: 'targets'
        },
        isArray: true
      },
      timeline: {
        method: 'GET',
        params: {
          action: 'timeline'
        },
        isArray: true
      },
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
