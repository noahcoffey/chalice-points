'use strict';

var LeaderboardCtrl = ['$scope', 'flash', 'users', 'leaderboardWeek', 'leaderboardAll', 'CPEvent', 'Leaderboard',
  function($scope, flash, users, leaderboardWeek, leaderboardAll, CPEvent, Leaderboard) {

  $scope.leaderboard = {
    week: leaderboardWeek,
    all: leaderboardAll
  };

  $scope.users = users;

  $scope.selected = {
    week: true,
    all: false
  };

  $scope.select = function(type) {
    for (var ctype in $scope.selected) {
      $scope.selected[ctype] = false;
    }
    $scope.selected[type] = true;
  };

  $scope.pointsAmount = 1;

  $scope.addEvent = function() {
    if ($scope.pointsTarget == $scope.current_user.name) {
      flash('alert', "Really? You can't give yourself points.");
      return;
    }

    $scope.pointsAmount = Math.max(Math.min($scope.current_user.max_points, $scope.pointsAmount), 1);

    var cpEvent = new CPEvent({
      target: $scope.pointsTarget,
      amount: $scope.pointsAmount,
      message: $scope.pointsMessage
    });

    cpEvent.$save(function(data) {
      flash('success', 'Chalice Point Given');

      $scope.pointsAmount = 1;
      $scope.pointsTarget = '';
      $scope.pointsMessage = '';

      var weekResult = Leaderboard.get({
        type: 'week'
      }, function() {
        $scope.leaderboard.week = weekResult;
      });

      var allResult = Leaderboard.get({
        type: 'all'
      }, function() {
        $scope.leaderboard.all = allResult;
      });
    });
  };
}];

LeaderboardCtrl.resolve = {
  leaderboardWeek: function($q, Leaderboard) {
    var deferred = $q.defer();
    var res = Leaderboard.get({
      type: 'week'
    }, function() {
      deferred.resolve(res);
    });
    return deferred.promise;
  },
  leaderboardAll: function($q, Leaderboard) {
    var deferred = $q.defer();
    var res = Leaderboard.get({
      type: 'all'
    }, function() {
      deferred.resolve(res);
    });
    return deferred.promise;
  },
  users: function($q, User) {
    var deferred = $q.defer();
    var res = User.query(function() {
      for (var i = res.length - 1; i >= 0; i--) {
        if (res[i].disabled) {
          res.splice(i, 1);
        }
      }

      deferred.resolve(res);
    });
    return deferred.promise;
  }
};

var ChartCtrl = ['$scope', '$routeParams', function($scope, $routeParams) {
  $scope.mode = $routeParams.mode ? $routeParams.mode.toLowerCase() : 'received';
  ChalicePoints.Chord($scope.mode);
}];

var WinnersCtrl = ['$scope', 'winners', function($scope, winners) {
  $scope.winners = winners;
}];

WinnersCtrl.resolve = {
  winners: function($q, Winner, $route) {
    var deferred = $q.defer();
    var res = Winner.query(function() {
      deferred.resolve(res);
    });

    return deferred.promise;
  }
};

var TimelineCtrl = ['$scope', 'timeline', function($scope, timeline) {
  $scope.timeline = timeline;
}];

TimelineCtrl.resolve = {
  timeline: function($q, Timeline, $route) {
    var deferred = $q.defer();
    var res = Timeline.query(function() {
      deferred.resolve(res);
    });

    return deferred.promise;
  }
};

var UserCtrl = ['$scope', '$routeParams', 'CPEvent', 'User', 'user', '$modal',
  function($scope, $routeParams, CPEvent, User, user, $modal) {
  $scope.user = user;

  $scope.predicate = 'name';
  $scope.reverse = false;

  $scope.editEvent = function(idx) {
    $scope.event = $scope.user.events[idx];

    var modal = $modal.open({
      templateUrl: '/public/partials/modals/edit_event.html',
      controller: EditEventModalCtrl,
      windowClass: 'small',
      resolve: {
        event: function() {
          return $scope.event;
        },
        users: function($q, User) {
          var deferred = $q.defer();
          var res = User.query(function() {
            for (var i = res.length - 1; i >= 0; i--) {
              if (res[i].disabled) {
                res.splice(i, 1);
              }
            }

            deferred.resolve(res);
          });
          return deferred.promise;
        }
      }
    });

    modal.result.then(function(evt) {
      CPEvent.update(null, evt);
    });
  };

  $scope.removeEvent = function(id) {
    if (!confirm('Are you sure you want to delete this event?')) {
      return false;
    }

    CPEvent.delete({}, {'id': id}, function(data) {
      $scope.user = User.get({
        userId: $scope.user.id
      });
    });
  };
}];

UserCtrl.resolve = {
  user: function($q, User, $route) {
    var deferred = $q.defer();
    var res = User.get({
      userId: $route.current.params.userId
    }, function() {
      deferred.resolve(res);
    });
    return deferred.promise;
  }
};

var ElderUsersCtrl = ['$scope', '$routeParams', 'User', 'users', '$modal',
  function($scope, $routeParams, User, users, $modal) {
    $scope.users = users;
    $scope.user = null;

    $scope.editUser = function(idx) {
      $scope.user = $scope.users[idx];

      var modal = $modal.open({
        templateUrl: '/public/partials/modals/edit_user.html',
        controller: EditUserModalCtrl,
        windowClass: 'tiny',
        resolve: {
          user: function() {
            return $scope.user;
          }
        }
      });

      modal.result.then(function(user) {
        User.update(null, user);
      });
    };

    $scope.removeUser = function(idx) {
      if (!confirm('Are you sure you want to delete this user?')) {
        return false;
      }

      User.delete({}, $scope.users[idx], function(data) {
        $scope.users.splice(idx, 1);
      });
    };

    $scope.mergeUser = function(idx) {
      $scope.user = $scope.users[idx];

      var modal = $modal.open({
        templateUrl: '/public/partials/modals/merge_user.html',
        controller: MergeUserModalCtrl,
        windowClass: 'tiny',
        resolve: {
          user: function() {
            return $scope.user;
          },
          users: function() {
            return $scope.users;
          }
        }
      });

      modal.result.then(function(merge) {
          User.merge(merge, function() {
            $scope.users.splice(idx, 1);
          });
      });
    };
}];

ElderUsersCtrl.resolve = {
  users: function($q, User, $route) {
    var deferred = $q.defer();
    var res = User.query({
      userId: 'all'
    }, function() {
      deferred.resolve(res);
    });
    return deferred.promise;
  }
};

var EditUserModalCtrl = ['$scope', '$modalInstance', 'user', function($scope, $modalInstance, user) {
  $scope.user = user;

  $scope.ok = function() {
    $modalInstance.close($scope.user);
  };

  $scope.cancel = function() {
    $modalInstance.dismiss('cancel');
  };
}];

var EditEventModalCtrl = ['$scope', '$modalInstance', 'event', 'users', function($scope, $modalInstance, event, users) {
  $scope.event = event;
  $scope.users = users;

  $scope.ok = function() {
    $modalInstance.close($scope.event);
  };

  $scope.cancel = function() {
    $modalInstance.dismiss('cancel');
  };
}];

var MergeUserModalCtrl = ['$scope', '$modalInstance', 'user', 'users', function($scope, $modalInstance, user, users) {
  $scope.user = user;
  $scope.users = angular.copy(users);
  $scope.merge = {
    id: $scope.user.id,
    target: null
  };

  for (var i = $scope.users.length - 1; i >= 0; i--) {
    if ($scope.users[i].id == $scope.user.id) {
      $scope.users.splice(i, 1);
      break;
    }
  }

  $scope.ok = function() {
    $modalInstance.close($scope.merge);
  };

  $scope.cancel = function() {
    $modalInstance.dismiss('cancel');
  };
}];
