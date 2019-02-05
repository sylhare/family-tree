group :frontend do
  guard :livereload do
    watch(%r{^app/.+\.(erb|haml)})
    watch(%r{^app/helpers/.+\.rb})
    watch(%r{^public/.+\.(css|js|html)})
    watch(%r{^config/locales/.+\.yml})
    # Rails Assets Pipeline
    watch(%r{(app|vendor)(/assets/\w+/(.+\.(css|js|html))).*}) do |m|
      "/assets/#{m[3]}"
    end
  end
end

group :backend do
  guard :bundler do
    watch('Gemfile')
  end

  guard :rspec, cmd: 'bundle exec spring rspec --drb --tag ~@seed', failed_mode: :none do
    watch('spec/spec_helper.rb')                                               { 'spec' }
    watch('app/controllers/application_controller.rb')                         { 'spec/controllers' }
    watch('config/routes.rb')                                                  { 'spec/routing' }
    watch(%r{^spec/support/(requests|controllers|mailers|models)_helpers\.rb}) { |m| "spec/#{m[1]}" }
    watch(%r{^spec/.+_spec\.rb})

    watch(%r{^app/controllers/(.+)_(controller)\.rb}) do |m|
      ["spec/routing/#{m[1]}_routing_spec.rb",
       "spec/#{m[2]}s/#{m[1]}_#{m[2]}_spec.rb",
       "spec/requests/#{m[1]}_spec.rb"]
    end

    watch(%r{^spec/factories/(.+)\.rb$})

    watch(%r{^app/(.+)\.rb}) { |m| "spec/#{m[1]}_spec.rb" }
    watch(%r{^lib/(.+)\.rb}) { |m| "spec/lib/#{m[1]}_spec.rb" }
  end
end

guard :rubocop, cli: ['--format', 'clang', '--display-cop-names', '--auto-correct', '--rails'] do
  watch(/.+\.rb$/)
  watch(%r{(?:.+/)?\.rubocop\.yml$}) { |m| File.dirname(m[0]) }
  watch(%r{(?:.+/)?\.rubocop_todo\.yml$}) { |m| File.dirname(m[0]) }
end
