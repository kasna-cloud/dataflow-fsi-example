import setuptools

setuptools.setup(
	name="app",
	version="0.1.0",
	install_requires=[
		"absl-py==0.12.0",
		"apache-beam[gcp]==2.29.0",
		"google-cloud-pubsub==1.7.0",
		"joblib==0.14.1",
		"pandas==1.2.4",
		"plotly==4.14.3",
		"pytest==6.2.4",
		"numpy==1.19.5",
		"scikit-learn==0.24.2",
		"tfx-bsl==0.29.0",
		"tfx==0.29.0",
	],
	packages=setuptools.find_packages(),
)
