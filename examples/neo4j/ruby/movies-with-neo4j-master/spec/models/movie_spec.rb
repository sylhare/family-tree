require 'rails_helper'

describe Movie do
  let(:movie_matrix)        { Movie.find_by title: 'The Matrix' }
  let(:the_matrix_reloaded) { Movie.find_by title: 'The Matrix Reloaded' }

  context 'properties' do
    let(:movie) { Movie.new(title: 'title', released: '2009', tagline: 'should be a great movie') }
    it 'allows to create a new movie' do
      expect { movie }.not_to raise_error
    end

    it 'has all the required properties' do
      expect(movie_matrix.title).to eq('The Matrix')
      expect(movie_matrix.released).to eq(1999)
      expect(movie_matrix.tagline).to eq('Welcome to the Real World')
    end
  end

  context '#people_in_movies' do
    let(:people_in_movies) { Movie.people_in_movies }

    context 'returns a hash' do
      it 'has movie id as key' do
        expect(people_in_movies.all? { |uuid, _| uuid.length == 36 }).to be true
      end
      it 'has the number of people as value' do
        expect(people_in_movies.all? { |_, count| count.class == Fixnum }).to be true
      end
    end

    it 'counts the people in the matrix' do
      count = Movie.people_in_movies[movie_matrix.uuid]
      expect(count).to eq(8)
    end

    it 'is faster than using movie.people.count' do
      movie_people_count = Benchmark.realtime do
        Movie.all.each { |m| m.people.count }
      end

      people_in_movies = Benchmark.realtime do
        p = Movie.people_in_movies
        Movie.all.each { |m| p[m.uuid] }
      end

      expect(people_in_movies).to be < movie_people_count
    end

    it 'is faster using neo4j-core than neo4j', performance: true do
      neo4j = Benchmark.realtime do
        Movie.as(:m).people(:p).pluck('m.uuid', 'count(p)').to_h
      end

      neo4j_core = Benchmark.realtime do
        Neo4j::Session.query(%{
          MATCH (p:Person)-[r]->(m:Movie)
          return m.uuid, count(m)
        }).map(&:to_a).to_h
      end

      expect(neo4j_core).to be < neo4j
    end
  end
end
