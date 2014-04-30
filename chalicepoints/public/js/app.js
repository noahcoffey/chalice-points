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
      '/chart': {
        templateUrl: '/public/partials/chart.html',
        controller: ChartCtrl
      },
      '/chart/:mode': {
        templateUrl: '/public/partials/chart.html',
        controller: ChartCtrl
      },
      '/user/:id': { 
        templateUrl: '/public/partials/profile.html',
        controller: UserCtrl,
        resolve: UserCtrl.resolve
      },
      '/winners': {
        templateUrl: '/public/partials/winners.html',
        controller: WinnersCtrl,
        resolve: WinnersCtrl.resolve
      },
      '/timeline': {
        templateUrl: '/public/partials/timeline.html',
        controller: TimelineCtrl,
        resolve: TimelineCtrl.resolve
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
