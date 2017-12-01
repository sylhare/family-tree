require 'rubygems'
require 'neography'
require 'sinatra'
require 'uri'

def create_graph
  neo = Neography::Rest.new
  graph_exists = neo.get_node_properties(0)
  return if graph_exists && graph_exists['name']

  names = %w[Max Agam Lester Musannif Adel Andrey Ryan James Bruce Tim Pinaki Mark Peter Anne Helene Corey Ben Rob Pramod Prasanna]

  commands = names.map{ |n| [:create_node, {"name" => n}]}
  names.each_index do |x| 
    commands << [:add_node_to_index, "nodes_index", "type", "User", "{#{x}}"]
    follows = names.size.times.map{|y| y}
    follows.delete_at(x)
    follows.sample(1 + rand(5)).each do |f|
      commands << [:create_relationship, "follows", "{#{x}}", "{#{f}}"]    
    end
  end

  batch_result = neo.batch *commands
end
  
def follower_matrix
  neo = Neography::Rest.new
  cypher_query =  " START a = node:nodes_index(type='User')"
  cypher_query << " MATCH a-[:follows]->b"
  cypher_query << " RETURN a.name, collect(b.name)"
  neo.execute_query(cypher_query)["data"]
end  

get '/follows' do
  follower_matrix.map{|fm| {"name" => fm[0], "follows" => fm[1][1..(fm[1].size - 2)]} }.to_json
end
