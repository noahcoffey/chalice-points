module.exports = (grunt) ->
  jsFiles = ['chalicepoints/public/js/**/*.js', '!chalicepoints/public/js/vendor/**/*']
  cssFiles = ['chalicepoints/public/css/**/*.css']

  grunt.initConfig
    concat:
      chalciepoints:
        files:
          'chalicepoints/public/js/chalicepoints.js': jsFiles
          'chalicepoints/public/css/chaliepoints.css': cssFiles
    jshint:
      files: jsFiles
      options:
        globalstrict: true
        '-W117': true
        browser: true
        devel: true
        jquery: true
    jsbeautifier:
      files: jsFiles
      options:
        indent_size: 2
    compass:
      chalicepoints:
        options:
          sassDir: 'chalicepoints/public/sass'
          cssDir: 'chalicepoints/public/css'
          noLineComments: true
          force: true
    watch:
      sass:
        files: ['chalicepoints/public/sass/**/*.scss']
        tasks: ['compass']
    uglify:
      chalicepoints:
        options:
          sourceMap: true
        files: [
          expand: true
          cwd: 'chalicepoints/public/js'
          src: ['**/*.js', '!**/*.min.js', '!**/*.src.js', '!vendor/**/*']
          dest: 'chalicepoints/public/js'
        ]
    cssmin:
      chalicepoints:
        expand: true
        cwd: 'chalicepoints/public/css'
        src: '**/*.css'
        dest: 'chalicepoints/public/css'

  grunt.loadNpmTasks 'grunt-contrib-jshint'
  grunt.loadNpmTasks 'grunt-contrib-clean'
  grunt.loadNpmTasks 'grunt-contrib-concat'
  grunt.loadNpmTasks 'grunt-jsbeautifier'
  grunt.loadNpmTasks 'grunt-contrib-compass'
  grunt.loadNpmTasks 'grunt-contrib-watch'
  grunt.loadNpmTasks 'grunt-contrib-uglify'
  grunt.loadNpmTasks 'grunt-contrib-cssmin'
  
  grunt.registerTask 'default', ['jshint', 'compass']
  grunt.registerTask 'precommit', ['jshint', 'compass']
  grunt.registerTask 'deploy', ['concat', 'uglify', 'cssmin']
