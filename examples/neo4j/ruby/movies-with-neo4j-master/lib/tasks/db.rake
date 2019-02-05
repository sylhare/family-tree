desc 'seed database'
namespace :db do
  task seed: [:environment] do
    seed = File.read File.join(Rails.root, 'db', 'seed.graph')
    Neo4j::Session.query seed
    Neo4j::Migration::AddIdProperty.new(Rails.root).migrate
  end
end
