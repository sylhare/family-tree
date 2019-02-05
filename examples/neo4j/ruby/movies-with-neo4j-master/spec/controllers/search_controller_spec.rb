require 'rails_helper'

describe SearchController, type: :controller do
  describe 'GET #index' do
    let(:top_gear) { Movie.find_by(title: 'Top Gun') }
    let(:people_in_movies) { Movie.people_in_movies }

    it 'returns http success' do
      get :index, q: 'Top'

      expect(response).to have_http_status(:success)
    end
    it 'assigns movies' do
      get :index, q: 'Top'

      expect(assigns(:movies)).to eq [top_gear]
    end

    it 'assigns people_in_movies' do
      get :index, q: 'Top'

      expect(assigns(:people_in_movies)).to eq people_in_movies
    end

    context 'when there is no search string' do
      it 'shows empty results' do
        get :index, q: ''

        expect(assigns(:movies)).to eq []
      end
    end
  end
end
