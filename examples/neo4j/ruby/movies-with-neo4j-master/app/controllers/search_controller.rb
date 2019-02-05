class SearchController < ApplicationController
  def index
    q = params[:q] || ''
    @movies = q.empty? ? [] : Movie.search(q)
    @people_in_movies = Movie.people_in_movies
  end
end
