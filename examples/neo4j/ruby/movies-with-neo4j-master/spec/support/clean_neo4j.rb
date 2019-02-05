require 'rails_helper'

RSpec.configure do |config|
  config.before(:all) do
  end
  config.before(:suite) do
    Neo4j::Session.current._query('MATCH (n) OPTIONAL MATCH (n)-[r]-() DELETE n,r')
    Rake::Task['db:seed'].invoke
  end
end
