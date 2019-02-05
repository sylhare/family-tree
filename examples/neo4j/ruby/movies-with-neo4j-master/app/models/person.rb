class Person
  include Neo4j::ActiveNode
  property :name
  property :born

  has_many :out, :movies, type: false

  has_many :out, :movies_acted_in, type: :ACTED_IN, model_class: :Movie
  has_many :out, :movies_directed, type: :DIRECTED, model_class: :Movie
  has_many :out, :movies_produced, type: :PRODUCED, model_class: :Movie
  has_many :out, :movies_wrote, type: :WROTE, model_class: :Movie

  def self.movies_by_people
    all(:p).movies(:m).pluck('p.uuid', 'count(m)').to_h
  end
end
