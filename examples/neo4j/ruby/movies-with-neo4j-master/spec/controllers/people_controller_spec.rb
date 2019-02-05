require 'rails_helper'

RSpec.describe PeopleController, type: :controller do
  let(:people) { Person.all.to_a }
  let(:keanu) { Person.find_by name: 'Keanu Reeves' }

  describe 'GET #index' do
    it 'returns http success' do
      get :index
      expect(response).to have_http_status(:success)
    end
  end

  describe 'GET #show' do
    it 'returns http success' do
      get :show, name: keanu.name
      expect(response).to have_http_status(:success)
    end
  end

  it 'assigns people' do
    get :index

    expect(assigns(:people)).to eq people
  end
end
