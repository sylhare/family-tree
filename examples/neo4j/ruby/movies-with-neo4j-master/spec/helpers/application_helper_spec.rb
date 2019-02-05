require 'rails_helper'

describe ApplicationHelper, type: :helper do
  let(:movie_matrix)        { Movie.find_by title: 'The Matrix' }

  context '#humanize_relation' do
    it 'converts a known relation type' do
      expect(helper.humanize_relation(:ACTED_IN)).to eq('acted')
    end

    it 'converts an unknown relation type' do
      expect(helper.humanize_relation(:SOMETHING_SOMETHING)).to eq('')
    end
  end
end
