import json
import os

import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, redirect, request
from refresh_git_data import get_build_details, deploy_build

from refresh_git_data import refresh_data, commit_info_file_path
from change_release_notes import fetch_all_tags, repoObject, get_all_features_across_repos, fetch_all_repos, \
    get_all_features_numbers


def init_refresh_data_scheduler():
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(func=refresh_data, trigger='cron', hour=1)
    scheduler.start()
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())


init_refresh_data_scheduler()

app = Flask(__name__)
port = int(os.getenv("PORT", 9099))


@app.route('/')
def tracker():
    with open(commit_info_file_path, 'r') as fp:
        data = json.load(fp)
    return render_template('home.html', commit_count=data, repo_length=len(data))


@DeprecationWarning
@app.route('/refresh_data')
def load_data():
    refresh_data(full_refresh=False)
    return redirect("/")

@app.route('/one-click-deployment-prelive', methods=["POST", "GET"])
def load_repos():
    repoList = ["fx-assembly-line-layout-ui-main-deploy-prelive"]
    if request.method == "POST":
        repositoryName = request.form.get("repository")
        if request.form['btn'] == "submit":
            repositoryName = request.form.get("repository")
            buildDetails = get_build_details(repositoryName)
            return render_template("one-click-deployment-prelive.html", repo_list=repoList, repo_length=len(repoList), buildDetails=buildDetails)
        if request.form['btn'] == "Deploy":
            repositoryName = request.form.get("repository")
            isBuildDeployed = deploy_build(repositoryName, 'main')
            buildDetails = get_build_details(repositoryName)
            if isBuildDeployed:
                message = "Application is getting deployed, Please wait for some time..."
            else:
                message = "Application deployment failed, Please try again later..."
            return render_template("one-click-deployment-prelive.html", repo_list=repoList, repo_length=len(repoList) , buildDetails=buildDetails, message=message)
    return render_template("one-click-deployment-prelive.html", repo_list=repoList, repo_length=len(repoList))

@app.route('/change-release-notes', methods=["POST", "GET"])
def load_repos_change_notes():
    global selectedrepositoryName
    global tag_old
    global tag_new
    global number_of_repo
    list_of_user_input = []
    number_of_repo = 1
    repoList = fetch_all_repos()
    if request.method == "POST":
        if request.form['btn'] == "submit":
            repositoryName = request.form.get("repository")
            selectedrepositoryName = repositoryName
            tagList = fetch_all_tags(repositoryName)
            return render_template("change-release-notes.html", repo_list=repoList, tag_list = tagList,repo_length=len(repoList), selected_repo= selectedrepositoryName,
            tag1="  ", tag2=" ")
        if request.form['btn'] == "ChangeNotes":
            list_of_multiple_repos =[]
            list_of_multiple_repos.append(repoObject('fx-demand-forecast-ui','v20221102-094434','v20221103-120435'))
            list_of_multiple_repos.append(repoObject('fx-demand-forecast-service','v20221025-064732','v20221111-035400'))
            if selectedrepositoryName:
                testRepo  = selectedrepositoryName
                tagList = fetch_all_tags(testRepo)
                tag_old = request.form.get("tag1")
                tag_new = request.form.get("tag2")
            list_of_user_input.append(repoObject(testRepo, tag_old, tag_new))
            getFeatures = get_all_features_across_repos(list_of_user_input)
            getStoryNumbers = get_all_features_numbers(list_of_user_input)

            get_all_features_numbers(list_of_multiple_repos)

            return render_template("change-release-notes.html", repo_list=repoList, repo_length=len(repoList), tag_list = tagList, feature_list=getFeatures,
                                   selected_repo= selectedrepositoryName,
                                   tag1=tag_old, tag2=tag_new, get_story_numbers=getStoryNumbers)
    return render_template("change-release-notes.html",repo_list=repoList, repo_length=len(repoList),)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
