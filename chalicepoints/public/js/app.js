(function() {
  'use strict';

  $(document).foundation();

  angular.module('chalicepoints', [
    'ngRoute',
    'ngAnimate',
    'mm.foundation',
    'chalicepoints.services',
    'chalicepoints.controllers',
    'chalicepoints.filters',
    'chalicepoints.directives'
  ])
  .config(['$routeProvider', '$locationProvider',
    function($routeProvider, $locationProvider) {
      $routeProvider
        .when('/', {
          templateUrl: '/public/partials/leaderboard.html',
          controller: 'LeaderboardController',
          controllerAs: 'leaderboardCtrl'
        })
        .when('/user/:id', {
          templateUrl: '/public/partials/profile.html',
          controller: 'UserController',
          controllerAs: 'userCtrl'
        })
        .when('/history', {
          templateUrl: '/public/partials/history.html',
          controller: 'HistoryController',
          controllerAs: 'historyCtrl'
        })
        .when('/users', {
          templateUrl: '/public/partials/elder/users.html',
          controller: 'ElderUsersController',
          controllerAs: 'elderUsersCtrl'
        })
        .otherwise({
          redirectTo: '/'
        });

      $locationProvider.html5Mode(true);
    }
  ])
  .run(['$rootScope', function($rootScope) {
    // Publish the user on the root scope.
    var user = document.getElementById('user');
    if (user) {
      user = angular.element(user);
      $rootScope.current_user = angular.fromJson(user.html());
    }
  }]);
})();
