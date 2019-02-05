class MoviesController < ApplicationController
  before_action :fetch_movies, only: [:index]

  def index
    @people_in_movies = Movie.people_in_movies
  end

  def show
    @movie = Movie.find_by(title: params[:title])
  end

  def fetch_movies
    @movies = Movie.all
  end
end
