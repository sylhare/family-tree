source 'https://rubygems.org'
ruby '2.1.2'
# Bundle edge Rails instead: gem 'rails', github: 'rails/rails'
gem 'rails', '4.2.3'
gem 'neo4j', '~> 5.0.0'
# Use SCSS for stylesheets
gem 'sass-rails', '~> 5.0'
# Use Uglifier as compressor for JavaScript assets
gem 'uglifier', '>= 1.3.0'
# Use CoffeeScript for .coffee assets and views
gem 'coffee-rails', '~> 4.1.0'
gem 'twitter-bootstrap-rails'

# Use jquery as the JavaScript library
gem 'jquery-rails'
# Turbolinks makes following links in your web application faster.
# Read more: https://github.com/rails/turbolinks
gem 'turbolinks'
# Build JSON APIs with ease. Read more: https://github.com/rails/jbuilder
gem 'jbuilder', '~> 2.0'
# bundle exec rake doc:rails generates the API under doc/api.
gem 'sdoc', '~> 0.4.0', group: :doc

gem 'puma'
gem 'rollbar', '~> 1.2.7'
group :development, :test do
  gem 'pry'
  gem 'pry-doc'
  gem 'pry-rails'
  gem 'byebug'
  # Access an IRB console on exception pages or by using <%= console %> in views
  gem 'web-console', '~> 2.0'
  gem 'spring'
  gem 'dotenv-rails'
end

gem 'haml'
gem 'foundation-rails'
group :development do
  gem 'rails_layout'
end

group :test do
  gem 'rspec'
  gem 'rspec-rails'
  gem 'spring-commands-rspec'
  gem 'fuubar'

  gem 'shoulda-matchers', require: false
  gem 'faker'
  gem 'capybara'
  gem 'capybara-webkit'
  gem 'simplecov', require: false
  gem 'fantaskspec'
  gem 'codeclimate-test-reporter'
end

group :development do
  gem 'guard'
  gem 'guard-rspec', require: false
  gem 'guard-bundler', require: false
  gem 'guard-shell', require: false
  gem 'guard-livereload', require: false
  gem 'guard-rubocop', require: false
  gem 'rb-fsevent', require: false
  gem 'rack-livereload'
  gem 'guard-spring'
end
