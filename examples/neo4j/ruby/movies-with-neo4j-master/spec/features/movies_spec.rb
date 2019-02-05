require 'rails_helper'

feature 'Movies' do
  scenario 'Browse movies' do
    visit '/movies'

    the_matrix = find(:xpath, "//div[@class='list-group']/a[@href='/movies/The%20Matrix']")
    expect(the_matrix.text).to eq 'The Matrix 8'

    click_link 'The Matrix 8'
    expect(page).to have_content('Welcome to the Real World')
  end
end
