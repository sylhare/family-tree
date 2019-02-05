require 'rails_helper'

describe MoviesController do
  let(:movies) { Movie.all.to_a }
  let(:people_in_movies) { Movie.people_in_movies }

  describe 'GET #index' do
    it 'returns http success' do
      get :index

      expect(response).to have_http_status(:success)
    end
    it 'assigns movies' do
      get :index

      expect(assigns(:movies)).to eq movies
    end

    it 'assigns people_in_movies' do
      get :index

      expect(assigns(:people_in_movies)).to eq people_in_movies
    end
  end

  describe 'GET #show' do
    let(:movie_matrix)        { Movie.find_by title: 'The Matrix' }

    it 'finds movie by title' do
      get :show, title: movie_matrix.title
      expect(response).to have_http_status(:success)
    end

    it 'renders the :show template' do
      get :show, title: movie_matrix.title
      expect(response).to render_template :show
    end

    it 'assigns movie' do
      get :show, title: movie_matrix.title
      expect(assigns(:movie)).to eq movie_matrix
    end
  end
end
