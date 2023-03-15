import React, {useState} from 'react'
import ControlledInput from "./ControlledInput";
import SearchNewsByTitleButton from "./SearchNewsByTitleButton";
import axios from "axios";
import appConfig from 'configs/app.config'
import {useSelector} from "react-redux";
import {useNavigate} from "react-router-dom";
import dateToString from "../../utils/dateToString";

const {apiPrefix} = appConfig

const trainGetClustersBaseUrl = 'http://localhost:8000/news-clustering/train-get-clusters'
const getSimilarNewsBaseUrl = 'http://localhost:8000/news-clustering/get-similar-news'


const HandleNewsOperations = () => {

    const [inputValue, setInputValue] = useState('');
    const [inputDisabled, setInputDisabled] = useState(false);
    const [loading, setLoading] = useState(false);

    const uid = useSelector((state) => state.auth.user.uid);
    let navigate = useNavigate();
    const sideNavCollapse = useSelector(state => state.theme.layout.sideNavCollapse)

    const onClick = () => {
        setLoading(true);
        setInputDisabled(true);
        console.log("Obtained URL: " + inputValue);

        let date7DaysAgo = new Date();
        date7DaysAgo.setDate(date7DaysAgo.getDate() - 7);

        const newsApiUrl = 'https://newsapi.org/v2/everything?' +
            'q=' + inputValue + '&' +
            'from=' + dateToString(date7DaysAgo, true, false) + '&' +
            'sortBy=popularity&' +
            'apiKey=a93ab4e177d84091af89c33507ad33d4';

        fetch(new Request(newsApiUrl))
            .then(response => response.json())
            .then(res => {
                // console.log("Got from News API: ");

                if (res.status === "ok") {
                    const searchedArticles = [...res.articles];

                    // console.log(res.articles);
                    // console.log(res.status);
                    // console.log(res.totalResults);

                    // 'news_json_obj': {news_url: {'title': str, 'content': str, 'contained_urls': {URL: URL_TITLE}}}

                    // TODO: First get the content of the URLs

                    const news_json_obj = {};
                    searchedArticles.forEach(article => {
                        news_json_obj[article.url] = {
                            title: "title1",  // TODO: Put in the title too
                            content: "content12039127",  // TODO: Put in the content too
                            contained_urls: {
                                // TODO: Put in the contained URLs too
                            },
                        }
                    });

                    fetch(new Request(trainGetClustersBaseUrl), {
                        method: "POST",
                        body: JSON.stringify({
                            news_json_obj: news_json_obj,
                            should_fit_similarity: true
                        }),
                        headers: {
                            "Content-Type": "application/json"
                        }
                    })
                    .then(response2 => response2.json())
                    .then(res2 => {
                        console.log(res2);

                        if (res2.status === "ok") {

                        }
                    });

                    //     r = requests.post(getSimilarNewsBaseUrl, json={
                    //         'url': 'https://www.bitdefender.com/blog/labs/5-times-more-coronavirus-themed-malware-reports-during-march/',
                    //         'title': "5 Times More Coronavirus-themed Malware Reports during March",
                    //         'content': test_news_content,
                    // # 'urls': None
                    // })

                    axios.post(
                        `${apiPrefix}/add-query-history`,
                        {
                            uid,
                            url: inputValue,
                            searchedArticles: searchedArticles,
                            // formedClusters: formedClusters,
                            // similarNews: similarNews
                        }
                    ).then(response => {
                        setLoading(false);
                        setInputDisabled(false);
                        setInputValue('');

                        navigate("/search-menu-news-query-history");
                    });
                }
            });
    }

    const inputContent =
        (
            <div className="grow">
                <ControlledInput
                    size="lg"
                    value={inputValue}
                    setValue={setInputValue}
                    onClick={onClick}
                    disabled={inputDisabled}
                />
            </div>
        )

    const buttonContent =
        (
            <SearchNewsByTitleButton
                size="lg"
                loading={loading}
                onClick={onClick}
            />
        )

    return (
        <>
            {
                sideNavCollapse ?
                    <div className="flex flex-col items-center space-x-8">
                        {/*<div className="flex flex-row items-center">*/}
                        <>{inputContent}</>
                        <>{buttonContent}</>
                        {/*</div>*/}
                    </div>
                    :
                    <div className="flex flex-row items-center h-40 space-x-8 ml-16 mr-16">
                        <>{inputContent}</>
                        <>{buttonContent}</>
                    </div>
            }
        </>
    )
}

export default HandleNewsOperations