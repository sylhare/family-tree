require 'rails_helper'

feature 'Movies' do
  scenario 'Browse people' do
    visit '/people'

    keanu_reeves = find(:xpath, "//a[contains(text(),'Keanu Reeves')]")
    expect(keanu_reeves.text).to eq 'Keanu Reeves 7'

    click_link 'Keanu Reeves 7'
    expect(page).to have_content('Keanu Reeves')
  end
end
