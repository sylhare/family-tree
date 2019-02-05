[![Code Climate](https://codeclimate.com/github/framallo/movies-with-neo4j/badges/gpa.svg)](https://codeclimate.com/github/framallo/movies-with-neo4j)

[![Test Coverage](https://codeclimate.com/github/framallo/movies-with-neo4j/badges/coverage.svg)](https://codeclimate.com/github/framallo/movies-with-neo4j/coverage)


# Movies rails application using Neo4j

This is a project example similar to [movies-ruby-neo4j-core](https://github.com/neo4j-examples/movies-ruby-neo4j-core) but using rails and the latest version of neo4j

# Why?

Because I wanted to update to the latest ruby library and I wanted to have tests in the example project.


# Setup

You need to start neo4j and set up the environment variable `NEO4J_URL`

```
neo4j start
echo NEO4J_URL=http://user:password@localhost:7474/ >> .env
```

Also, you need to install and setup the test database

```
rake neo4j:install[community-2.2.4,test]
rake neo4j:config[test,7475]
echo NEO4J_URL=http://localhost:7475/ >> .env.test
```

# Test

In order to run the test suite you need to run a [test instance of neo4j](https://github.com/neo4jrb/neo4j/wiki/How-To-Test)

```
rake neo4j:start[test]
guard
```

I am skipping the seed tests with Guard, but you can test the seed task manually with

```
rspec spec/lib/tasks/db_spec.rb
```

# Issues

## installing liibv8

run this command. You can read more [here](https://github.com/cowboyd/libv8/issues/169)

```
gem install libv8 -v '3.16.14.11' -- --with-system-v8
```

## Neo4j configuration error

If your username or password is incorrect you might get this error

```
resource.rb:37:in `handle_response_error!': Expected response code 200 Error for request
```
