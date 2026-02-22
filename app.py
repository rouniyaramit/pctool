import streamlit as st

# Set the page title and icon
st.set_page_config(page_title="Coming Soon", page_icon="⏳")

# Use columns to center the content
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.image("https://cdn-icons-png.flaticon.com/512/4461/4461841.png", width=100)
    st.title("Project Name")
    st.header("Coming Soon")
    st.write("---")
    st.write("We are working hard to bring you something amazing. Stay tuned!")
    
    # Optional: Add a progress bar for visual effect
    st.info("Development Progress")
    # st.progress(75)

    # Optional: Email signup simulation
    # email = st.text_input("Get notified when we launch:", placeholder="rouniyaramit@gmail.com")
    # if st.button("Notify Me"):
        # if email:
            # st.success("Thanks! We'll keep you updated.")
        # else:
            # st.warning("Please enter a valid email.")




