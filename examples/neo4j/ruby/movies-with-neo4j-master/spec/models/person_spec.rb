require 'rails_helper'

describe Person do
  context 'properties' do
    let(:keanu) { Person.new(name: 'Keanu Reeves', born: 1964) }

    it 'allows to create a new movie' do
      expect { keanu }.not_to raise_error
    end

    it 'has all the required properties' do
      expect(keanu.name).to eq('Keanu Reeves')
      expect(keanu.born).to eq(1964)
    end
  end

  context '#movies_by_people' do
    let(:movies_by_people) { Person.movies_by_people }
    let(:keanu) { Person.find_by name: 'Keanu Reeves' }

    it 'has movie id as key' do
      expect(movies_by_people.all? { |uuid, _| uuid.length == 36 }).to be true
    end
    it 'has the number of people as value' do
      expect(movies_by_people.all? { |_, count| count.class == Fixnum }).to be true
    end

    it 'counts the movies by Keanu Reeves' do
      count = movies_by_people[keanu.uuid]
      expect(count).to eq(7)
    end
  end

  it 'is faster than using person.movies.count' do
    movie_people_count = Benchmark.realtime do
      Person.all.each { |m| m.movies.count }
    end

    movies_by_people = Benchmark.realtime do
      m = Person.as(:p).movies(:m).pluck('p.uuid', 'count(p)').to_h
      Person.all.each { |p| m[p.uuid] }
    end

    expect(movies_by_people).to be < movie_people_count
  end

  it 'is faster using neo4j-core than neo4j', performance: true do
    neo4j = Benchmark.realtime do
      Person.as(:p).movies(:m).pluck('p.uuid', 'count(p)').to_h
    end

    neo4j_core = Benchmark.realtime do
      Neo4j::Session.query(%{
        MATCH (p:Person)-[r]->(m:Movie)
        return p.uuid, count(p)
      }).map(&:to_a).to_h
    end

    expect(neo4j_core).to be < neo4j
  end
end
