require 'rails_helper'

feature 'Movies' do
  scenario 'Browse movies' do
    visit '/'
    fill_in 'Search', with: 'Top'
    click_button 'Submit'

    expect(page).to have_css('.list-group-item', count: 1)
  end
end
