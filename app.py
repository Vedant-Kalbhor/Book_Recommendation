from flask import Flask, render_template, request
import pickle
import numpy as np
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load objects from pickle files
try:
    with open('popular.pkl', 'rb') as f:
        popular_df = pickle.load(f)
    with open('pt.pkl', 'rb') as f:
        pt = pickle.load(f)
    with open('books.pkl', 'rb') as f:
        books = pickle.load(f)
    with open('similarity_scores.pkl', 'rb') as f:
        similarity_scores = pickle.load(f)
    
    # Pre-process books to keep only columns we need and remove duplicates
    # This saves memory and speeds up lookups
    books = books[['Book-Title', 'Book-Author', 'Image-URL-M']].drop_duplicates('Book-Title')
    logger.info("Data loaded successfully.")
except Exception as e:
    logger.error(f"Error loading data: {e}")
    popular_df = pt = books = similarity_scores = None

app = Flask(__name__)

# Cache for faster lookup
# Use lower() to make it case-insensitive
if pt is not None:
    book_index_map = {book.lower(): idx for idx, book in enumerate(pt.index)}
else:
    book_index_map = {}

@app.route('/')
def index():
    if popular_df is None:
        return "Internal Server Error: Could not load data.", 500
        
    return render_template(
        'index.html',
        book_name=list(popular_df['Book-Title'].values),
        author=list(popular_df['Book-Author'].values),
        image=list(popular_df['Image-URL-M'].values),
        votes=list(popular_df['num_ratings'].values),
        rating=list(popular_df['avg_rating'].values)
    )

@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')

@app.route('/recommend_books', methods=['POST'])
def recommend():
    try:
        user_input = request.form.get('user_input')
        
        if not user_input:
            return render_template('recommend.html', error="Please enter a book name.")

        user_input_lower = user_input.strip().lower()

        if user_input_lower not in book_index_map:
            return render_template(
                'recommend.html',
                error=f"Book '{user_input}' not found. Please try another title."
            )

        index = book_index_map[user_input_lower]
        
        # Get similar items
        # similarity_scores[index] is the row of similarities for this book
        distances = similarity_scores[index]
        similar_items = sorted(
            list(enumerate(distances)),
            key=lambda x: x[1],
            reverse=True
        )[1:6]

        data = []
        for i in similar_items:
            # pt.index[i[0]] is the title of the similar book
            title = pt.index[i[0]]
            temp_df = books[books['Book-Title'] == title]
            
            if not temp_df.empty:
                # Add title, author, and image URL
                item = [
                    temp_df['Book-Title'].values[0],
                    temp_df['Book-Author'].values[0],
                    temp_df['Image-URL-M'].values[0]
                ]
                data.append(item)
        
        logger.info(f"Recommendations for '{user_input}' generated successfully.")
        return render_template('recommend.html', data=data)

    except Exception as e:
        logger.error(f"Error in recommendation for input '{user_input}': {e}")
        return render_template('recommend.html', error="An unexpected error occurred. Please try again.")

if __name__ == '__main__':
    app.run(debug=True)