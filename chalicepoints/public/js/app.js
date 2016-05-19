(function() {
  'use strict';

  $(document).foundation();

  var routeConfig = {
    defaultRoute: '/',
    routes: {
      '/': {
        templateUrl: '/public/partials/leaderboard.html',
        controller: LeaderboardCtrl,
        resolve: LeaderboardCtrl.resolve
      },
      '/user/:id': { 
        templateUrl: '/public/partials/profile.html',
        controller: UserCtrl,
        resolve: UserCtrl.resolve
      },
      '/history': {
        templateUrl: '/public/partials/history.html',
        controller: HistoryCtrl
      },
      '/users': {
        templateUrl: '/public/partials/elder/users.html',
        controller: ElderUsersCtrl,
        resolve: ElderUsersCtrl.resolve
      }
    }
  };

  var app = angular.module('chalicepoints', [
    'ngRoute',
    'chalicepoints.services',
    'chalicepoints.filters',
    'chalicepoints.directives',
    'mm.foundation'
  ]);

  app.config(['$routeProvider', '$locationProvider',
    function($routeProvider, $locationProvider) {
      if (routeConfig.routes !== undefined) {
        angular.forEach(routeConfig.routes, function(route, path) {
            $routeProvider.when(path, route);
        });
      }

      if (routeConfig.defaultRoute !== undefined) {
        $routeProvider.otherwise({
          redirectTo: routeConfig.defaultRoute
        });
      }

      $locationProvider.html5Mode(true);
    }
  ]);

  app.run(['$rootScope', function($rootScope) {
    // Publish the user on the root scope.
    var user = document.getElementById('user');
    if (user) {
      user = angular.element(user);
      $rootScope.current_user = angular.fromJson(user.html());
    }
  }]);
})();
