class CommentsController < ApplicationController
  before_action :set_comment, only: [:show, :edit, :update, :destroy]
  before_action :set_post, only: [:show, :edit, :update, :destroy, :create]

  def index
    @comments = Comment.all
  end

  def edit
  end

  def create
    @comment = Comment.new(comment_params)

    if @comment.save
      @post.comments << @comment
      #No foreign keys, so have to manually push it into the :comments relation array
      redirect_to @post, notice: 'Comment was successfully created.'
    else
      render :new
    end
  end

  def update
    if @comment.update(comment_params)
      redirect_to @post, notice: 'Comment was successfully updated'
    else
      render 'edit'
    end
  end

  def destroy
    @comment.destroy
    redirect_to @post
  end

  private
    def set_comment
      @comment = Comment.find(params[:id])
    end

    def comment_params
      params[:comment]
    end

    def set_post
      @post = Post.find(params[:post_id])
    end
end
