class PeopleController < ApplicationController
  def index
    @people = Person.all
    @movies_by_people = Person.movies_by_people
  end

  def show
    @person = Person.find_by(name: params[:name])
  end
end
