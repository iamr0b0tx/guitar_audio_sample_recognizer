def main():
    latest_model = get_latest_model()

    # get audio file info
    audio_sample_label = instance.audio_sample_label.label
    audio_file_path = instance.audio.name

    # retrieve audio file from the cloud
    audio_file_object = cloudinary_raw_storage_object.open(audio_file_path)
    audio_local_file_path = os.path.join(
        "media",
        default_storage.save(audio_file_path, ContentFile(audio_file_object.read()))
    )

    # fit it to model
    latest_model.fit([extract_features(audio_local_file_path)], [audio_sample_label])

    # save model locally
    model_local_file_path = "knn_model.joblib"
    joblib.dump(latest_model, model_local_file_path)

    # new recognizer model instance
    new_model_instance = AudioSampleRecognizerModel.objects.create(model=model_local_file_path)

    # move model to the cloud
    with open(model_local_file_path, 'rb') as f:
        new_model_instance.model.save("knn_model.joblib", File(f))


if __name__ == '__main__':
    main()