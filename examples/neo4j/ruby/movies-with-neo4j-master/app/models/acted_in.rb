class ActedIn
  include Neo4j::ActiveRel

  from_class :Person
  to_class :Movie

  property :roles

  def rel_type
    type
  end
end
