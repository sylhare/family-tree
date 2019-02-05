module ApplicationHelper
  def relationship_to_human
    { ACTED_IN: 'acted' }
  end

  def humanize_relation(relationship)
    relationship_to_human[relationship] || ''
  end
end
