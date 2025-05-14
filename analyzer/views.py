# analyzer/views.py
from django.shortcuts import render
from django.core.files.storage import default_storage
from analyzer.utils.preprocessor import preprocess
from analyzer.utils.helper import (
    fetch_stats, monthly_timeline, daily_timeline, week_activity_map,
    month_activity_map, activity_heatmap, most_busy_users, create_wordcloud,
    most_common_words, emoji_helper
)
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import logging

# Set up logging
logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'analyzer/introduction.html')

def upload_chat(request):
    if request.method == 'POST' and request.FILES['chat_file']:
        try:
            # Get the selected format
            chat_format = request.POST.get('chat_format')

            # Save the uploaded file
            chat_file = request.FILES['chat_file']
            file_path = default_storage.save(chat_file.name, chat_file)
            
            # Read the file content in binary mode
            with default_storage.open(file_path, 'rb') as file:
                chat_data = file.read().decode('utf-8')  # Decode using UTF-8
            
            # Preprocess the chat data based on the selected format
            df = preprocess(chat_data, chat_format)

            # Check if the DataFrame is empty
            if df.empty:
                return render(request, 'analyzer/upload.html', {'error': 'No valid data found in the chat file.'})

            # Fetch unique users
            user_list = df['user'].unique().tolist()
            if 'group_notification' in user_list:
                user_list.remove('group_notification')
            user_list.sort()
            user_list.insert(0, "Overall")

            # Get the selected user from the form
            selected_user = request.POST.get('selected_user', 'Overall')

            # Fetch statistics
            num_messages, num_words, num_media_messages, num_links = fetch_stats(selected_user, df)

            # Monthly timeline
            timeline = monthly_timeline(selected_user, df)

            # Daily timeline
            daily_timeline_data = daily_timeline(selected_user, df)

            # Activity map
            busy_day = week_activity_map(selected_user, df)
            busy_month = month_activity_map(selected_user, df)

            # Weekly Activity Heatmap
            user_heatmap = activity_heatmap(selected_user, df)

            # Most busy users
            if selected_user == 'Overall':
                x, new_df = most_busy_users(df)

            # WordCloud
            df_wc = create_wordcloud(selected_user, df)

            # Most common words
            most_common_df = most_common_words(selected_user, df)

            # Emoji Analysis
            emoji_df = emoji_helper(selected_user, df)

            # Convert plots to base64 for rendering in templates
            def plot_to_base64(fig):
                buf = io.BytesIO()
                fig.savefig(buf, format='png', bbox_inches='tight')
                buf.seek(0)
                return base64.b64encode(buf.read()).decode('utf-8')

            # Monthly timeline plot
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(timeline['time'], timeline['message'], color='green')
            plt.xticks(rotation=45, fontsize=10)
            plt.yticks(fontsize=10)
            plt.xlabel('Time', fontsize=12)
            plt.ylabel('Messages', fontsize=12)
            plt.title('Monthly Timeline', fontsize=14)
            plt.tight_layout()
            monthly_timeline_plot = plot_to_base64(fig)
            plt.close()

            # Daily timeline plot
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(daily_timeline_data['only_date'], daily_timeline_data['message'], color='black')
            plt.xticks(rotation=45, fontsize=10)
            plt.yticks(fontsize=10)
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Messages', fontsize=12)
            plt.title('Daily Timeline', fontsize=14)
            plt.tight_layout()
            daily_timeline_plot = plot_to_base64(fig)
            plt.close()

            # Busy day plot
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(busy_day.index, busy_day.values, color='purple')
            plt.xticks(rotation=45, fontsize=10)
            plt.yticks(fontsize=10)
            plt.xlabel('Day', fontsize=12)
            plt.ylabel('Messages', fontsize=12)
            plt.title('Most Busy Day', fontsize=14)
            plt.tight_layout()
            busy_day_plot = plot_to_base64(fig)
            plt.close()

            # Busy month plot
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(busy_month.index, busy_month.values, color='orange')
            plt.xticks(rotation=45, fontsize=10)
            plt.yticks(fontsize=10)
            plt.xlabel('Month', fontsize=12)
            plt.ylabel('Messages', fontsize=12)
            plt.title('Most Busy Month', fontsize=14)
            plt.tight_layout()
            busy_month_plot = plot_to_base64(fig)
            plt.close()

            # Heatmap plot
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(user_heatmap, ax=ax, cmap="coolwarm")
            plt.xticks(fontsize=10)
            plt.yticks(fontsize=10)
            plt.xlabel('Period', fontsize=12)
            plt.ylabel('Day', fontsize=12)
            plt.title('Weekly Activity Heatmap', fontsize=14)
            plt.tight_layout()
            heatmap_plot = plot_to_base64(fig)
            plt.close()

            # WordCloud plot
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.imshow(df_wc)
            ax.axis("off")
            plt.tight_layout()
            wordcloud_plot = plot_to_base64(fig)
            plt.close()

            # Most common words plot
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh(most_common_df[0], most_common_df[1], color='blue')
            plt.xticks(fontsize=10)
            plt.yticks(fontsize=10)
            plt.xlabel('Frequency', fontsize=12)
            plt.ylabel('Words', fontsize=12)
            plt.title('Most Common Words', fontsize=14)
            plt.tight_layout()
            common_words_plot = plot_to_base64(fig)
            plt.close()

            # Emoji pie chart
            if not emoji_df.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.pie(emoji_df["Count"].head(), labels=emoji_df["Emoji"].head(), autopct="%0.2f", textprops={'fontsize': 12})
                plt.title('Emoji Analysis', fontsize=14)
                plt.tight_layout()
                emoji_plot = plot_to_base64(fig)
                plt.close()
            else:
                emoji_plot = None

            # Prepare context for the template
            context = {
                'num_messages': num_messages,
                'num_words': num_words,
                'num_media_messages': num_media_messages,
                'num_links': num_links,
                'monthly_timeline_plot': monthly_timeline_plot,
                'daily_timeline_plot': daily_timeline_plot,
                'busy_day_plot': busy_day_plot,
                'busy_month_plot': busy_month_plot,
                'heatmap_plot': heatmap_plot,
                'wordcloud_plot': wordcloud_plot,
                'common_words_plot': common_words_plot,
                'emoji_plot': emoji_plot,
                'user_list': user_list,
                'selected_user': selected_user,
                'most_busy_users_df': new_df if selected_user == 'Overall' else None,
                'emoji_df': emoji_df,
            }

            return render(request, 'analyzer/results.html', context)
        
        except UnicodeDecodeError as e:
            logger.error(f"UnicodeDecodeError: {e}")
            return render(request, 'analyzer/upload.html', {'error': 'The file contains invalid characters. Please ensure the file is encoded in UTF-8.'})
        except Exception as e:
            logger.error(f"Error processing the file: {e}")
            return render(request, 'analyzer/upload.html', {'error': f'Error processing the file: {e}'})
    
    return render(request, 'analyzer/upload.html')