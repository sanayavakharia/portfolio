# %%
import gzip
from collections import defaultdict
import numpy as np

# Load and process the gzip file
def load_gzip_file(file_path):
    with gzip.open(file_path, 'rt') as file:
        for line in file:
            yield eval(line)

# Load the dataset from CSV format
def load_csv_data(file_path):
    with gzip.open(file_path, 'rt') as file:
        next(file)  # Skip header
        for line in file:
            user_id, book_id, rating = line.strip().split(',')
            yield user_id, book_id, int(rating)

# Calculate Jaccard similarity between two sets
def compute_jaccard_similarity(set1, set2):
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0

# Split the data into training and validation sets
def prepare_data():
    all_user_ratings = list(load_csv_data("train_Interactions.csv.gz"))
    training_data = all_user_ratings[:200000]
    validation_data = all_user_ratings[200000:]
    return training_data, validation_data, all_user_ratings

# Build the collaborative filtering model
def build_model(training_data, all_user_ratings):
    user_item_ratings = defaultdict(list)
    item_user_ratings = defaultdict(list)

    # Populate user-item and item-user mappings
    for user, book, rating in training_data:
        user_item_ratings[user].append((book, rating))
        item_user_ratings[book].append((user, rating))

    all_ratings = [rating for _, _, rating in training_data]
    global_avg_rating = np.mean(all_ratings)

    # Initialize biases
    global_bias = global_avg_rating
    user_bias = defaultdict(float)
    item_bias = defaultdict(float)
    reg_param = 5.0  # Regularization parameter

    # Optimize biases
    def optimize_biases():
        nonlocal global_bias
        global_bias = sum(
            rating - (user_bias[user] + item_bias[book])
            for user, book, rating in training_data
        ) / len(training_data)

        for user in user_item_ratings:
            user_bias[user] = sum(
                rating - (global_bias + item_bias[book])
                for book, rating in user_item_ratings[user]
            ) / (reg_param + len(user_item_ratings[user]))

        for book in item_user_ratings:
            item_bias[book] = sum(
                rating - (global_bias + user_bias[user])
                for user, rating in item_user_ratings[book]
            ) / (reg_param + len(item_user_ratings[book]))

        mse = np.mean([
            (rating - (global_bias + user_bias[user] + item_bias[book])) ** 2
            for user, book, rating in training_data
        ])
        return mse

    for _ in range(30):
        optimize_biases()

    # Gather metadata for predictions
    all_users = {user for user, _, _ in all_user_ratings}
    all_books = {book for _, book, _ in all_user_ratings}
    interactions = {(user, book) for user, book, _ in all_user_ratings}

    # Book popularity statistics
    book_read_counts = defaultdict(int)
    total_interactions = sum(1 for _ in load_csv_data("train_Interactions.csv.gz"))
    for _, book, _ in load_csv_data("train_Interactions.csv.gz"):
        book_read_counts[book] += 1

    sorted_books = sorted(book_read_counts.items(), key=lambda x: -x[1])
    top_books = set()
    cumulative_count = 0
    for book, count in sorted_books:
        cumulative_count += count
        top_books.add(book)
        if cumulative_count > 1.5 * total_interactions / 2:
            break

    return (global_bias, user_bias, item_bias, user_item_ratings,
            item_user_ratings, interactions, book_read_counts, top_books, global_avg_rating)

# Predict a user's rating for a book
def predict_user_rating(user, book, model):
    (global_bias, user_bias, item_bias, user_ratings, item_ratings,
     _, _, _, avg_rating) = model

    if user in user_bias and book in item_bias:
        return max(1, min(5, global_bias + user_bias[user] + item_bias[book]))

    if user in user_ratings:
        return np.mean([rating for _, rating in user_ratings[user]])

    if book in item_ratings:
        return np.mean([rating for _, rating in item_ratings[book]])

    return avg_rating

# Predict whether a user will read a book
def predict_read_action(user, book, model):
    (_, _, _, user_ratings, item_ratings, interactions, book_counts, top_books, _) = model

    if book in top_books:
        return 1

    max_similarity = 0
    if user in user_ratings:
        current_users = {u for u, _ in item_ratings.get(book, [])}
        for other_book, _ in user_ratings[user]:
            compared_users = {u for u, _ in item_ratings.get(other_book, [])}
            max_similarity = max(max_similarity, compute_jaccard_similarity(current_users, compared_users))

    if max_similarity > 0.025 or len(item_ratings.get(book, [])) > 40:
        return 1

    return 0

# Execute predictions for ratings and reading actions
def execute_predictions():
    print("Preparing data...")
    training_data, _, all_user_ratings = prepare_data()

    print("Training model...")
    model = build_model(training_data, all_user_ratings)

    print("Running rating predictions...")
    with open("predictions_Rating.csv", 'w') as rating_file:
        rating_file.write("userID,bookID,prediction\n")
        for line in open("pairs_Rating.csv"):
            if line.startswith("userID"):
                continue
            user, book = line.strip().split(',')
            predicted_rating = predict_user_rating(user, book, model)
            rating_file.write(f"{user},{book},{predicted_rating:.1f}\n")

    print("Running read predictions...")
    with open("predictions_Read.csv", 'w') as read_file:
        read_file.write("userID,bookID,prediction\n")
        for line in open("pairs_Read.csv"):
            if line.startswith("userID"):
                continue
            user, book = line.strip().split(',')
            predicted_read = predict_read_action(user, book, model)
            read_file.write(f"{user},{book},{predicted_read}\n")

execute_predictions()

# %%



