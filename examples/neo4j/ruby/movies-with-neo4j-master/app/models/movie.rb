class Movie
  include Neo4j::ActiveNode
  property :title
  property :released
  property :tagline

  has_many :in, :people, type: false
  has_many :in, :actors, type: :ACTED_IN, model_class: :Person
  has_many :in, :directors, type: :DIRECTED, model_class: :Person
  has_many :in, :producers, type: :PRODUCED, model_class: :Person
  has_many :in, :writers, type: :WROTE, model_class: :Person

  scope :search, -> (query) { where(title: Regexp.new("(?i).*#{query}.*")) }

  def self.people_in_movies
    all(:m).people(:p).pluck('m.uuid', 'count(p)').to_h
  end
end
