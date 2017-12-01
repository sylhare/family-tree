# README


A sample template application using Rails and Neo4j. Demonstrates simple RESTful features of a typical rails app. 
Documentation here will serve as a guide for setting up Neo4j for future uses.

### Dependencies

Note: I have only tested this method using Ubuntu 14.04 LTS 64 bit.

* Jruby 1.7.12
* Rails 4.1
* OpenJDK 64-Bit Server VM
* Neo4j.rb v3.0 (unstable alpha but seems to work so far)

### Setup

Changes to the database schema are done through class models. Migrations are not utilized with Neo4j, and any changes made to properties via `property` in models will be immediately available (note: this can have screwy after effects. I've always had to wipe the database if I make any `property` changes.)

1. Clone project
2. Install and switch to jruby
 
 `rvm install jruby-1.7.12`

 `rvm use jruby-1.7.12`

3. Run `bundle` to install gems
4. Start neo4j

    `rake neo4j:install[community-2.0.2]`

    `rake neo4j:start`
    
    You should be able to start `rails server` and also utilize the Neo4j dashboard at `localhost:7474`

### Deploy with Heroku
1. Modify `config/application.rb`
2. 
	```
	config.neo4j.session_type = :server_db
	config.neo4j.session_path = ENV["GRAPHENEDB_URL"] ||'http://localhost:7474'
	```
	
2. Ensure working application is deployed to git repo
3. Create a new heroku application

	`heroku apps:create --stack cedar`
	
	`heroku addons add graphenedb`
4. Push to heroku

    `git push heroku master`
5. Access Neo4j Web Admin Interface

	open the url displayed from `heroku config:get GRAPHENEDB_URL`

	You can also access configuration options with `heroku addons:open graphenedb`


### Resources

* https://github.com/andreasronge/neo4j/wiki/Neo4j-v3

* https://devcenter.heroku.com/articles/graphenedb

* http://docs.neo4j.org/

* http://geekmonkey.org/articles/25-using-neo4j-with-rails-3-2
