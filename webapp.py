# For potato leaf disease prediction
import streamlit as st
from PIL import Image
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title('Potato Leaf Disease Prediction')


@st.cache_resource
def load_classifier_model():
    return tf.keras.models.load_model(r'final_model.h5', compile=False)


def main():
    file_uploaded = st.file_uploader('Choose an image...', type='jpg')
    if file_uploaded is not None:
        image = Image.open(file_uploaded).convert("RGB")
        st.write("Uploaded Image.")
        figure = plt.figure()
        plt.imshow(image)
        plt.axis('off')
        st.pyplot(figure)
        result, confidence = predict_class(image)
        st.write('Prediction : {}'.format(result))
        st.write('Confidence : {}%'.format(confidence))


def predict_class(image):
    with st.spinner('Loading Model...'):
        classifier_model = load_classifier_model()

    test_image = image.resize((256, 256))
    test_image = tf.keras.utils.img_to_array(test_image)
    test_image = test_image / 255.0
    test_image = np.expand_dims(test_image, axis=0)

    class_name = ['Potato__Early_blight', 'Potato__Late_blight', 'Potato__healthy']

    prediction = classifier_model.predict(test_image, verbose=0)
    confidence = round(100 * np.max(prediction[0]), 2)
    final_pred = class_name[np.argmax(prediction)]

    return final_pred, confidence


footer = """<style>
a:link , a:visited{
    color: white;
    background-color: transparent;
    text-decoration: None;
}

a:hover,  a:active {
    color: red;
    background-color: transparent;
    text-decoration: None;
}

.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: transparent;
    color: black;
    text-align: center;
}
</style>

<div class="footer">
<p align="center"> <a href="https://www.linkedin.com/in/ronylpatil/">Developed with ❤ by ronil</a></p>
</div>
        """

st.markdown(footer, unsafe_allow_html=True)

if __name__ == '__main__':
    main()