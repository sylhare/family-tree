require 'rails_helper'

describe 'db:seed', type: :rake, seed: true do
  it { is_expected.to depend_on(:environment) }

  it 'populates the database' do
    person_count = Person.count
    movie_count  = Movie.count

    subject.execute
    expect(Person.count - person_count).to eq(131)
    expect(Movie.count - movie_count).to eq(38)
  end

  it 'populates uuid fields' do
    expect(Movie.where(uuid: nil).count).to eq 0
    expect(Person.where(uuid: nil).count).to eq 0
  end
end
