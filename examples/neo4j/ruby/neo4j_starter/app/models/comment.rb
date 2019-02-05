class Comment
    include Neo4j::ActiveNode
    property :author, :type => String
    property :email, :type => String  
    property :content, :type => String
    property :created_at

    has_one(:post).from(:comments)    

    index :author
end