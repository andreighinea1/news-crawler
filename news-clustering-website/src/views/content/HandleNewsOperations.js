import React, {useState} from 'react'
import ControlledInput from "./ControlledInput";
import SearchNewsByTitleButton from "./SearchNewsByTitleButton";
import axios from "axios";
import appConfig from 'configs/app.config'
import {useSelector} from "react-redux";
import {useNavigate} from "react-router-dom";

const {apiPrefix} = appConfig

const trainGetClustersBaseUrl = 'http://localhost:8000/news-clustering/train-get-clusters'


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
        console.log("Obtained Search Query: " + inputValue);

        // let date7DaysAgo = new Date();
        // date7DaysAgo.setDate(date7DaysAgo.getDate() - 7);

        // let date29DaysAgo = new Date();
        // date29DaysAgo.setDate(date29DaysAgo.getDate() - 29);

        const newsApiUrl = 'https://newsapi.org/v2/everything?' +
            'q=' + inputValue + '&' +
            // 'from=' + dateToString(date29DaysAgo, true, false) + '&' +
            'from=2023-02-14&' +
            'sortBy=popularity&' +
            'apiKey=a93ab4e177d84091af89c33507ad33d4';

        // Query the News API
        fetch(new Request(newsApiUrl))
            .then(response => response.json())
            .then(res => {
                // console.log("Got from News API: ");

                if (res.status === "ok") {
                    const searchedArticles = [...res.articles];

                    if (searchedArticles.length > 0) {
                        // Get the clusters from the news
                        const news_json_obj = {};
                        searchedArticles.forEach(article => {
                            news_json_obj[article.url] = {
                                title: article.title,
                                content: article.content,
                                contained_urls: {
                                    // TODO: Put in the contained URLs too
                                },
                            };
                        });

                        let formedClusters = undefined;
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
                                if (res2) {
                                    formedClusters = [...res2.clusters];
                                    console.log("Found clusters:");
                                    console.log(formedClusters);
                                }

                                // Add to the query history
                                axios.post(
                                    `${apiPrefix}/add-query-history`,
                                    {
                                        uid,
                                        searchQuery: inputValue,
                                        searchedArticles,
                                        formedClusters,
                                    }
                                ).then(response3 => {
                                    setLoading(false);
                                    setInputDisabled(false);
                                    setInputValue('');

                                    navigate("/search-menu-news-query-history");
                                });
                            });
                    } else {
                        setLoading(false);
                        setInputDisabled(false);
                        setInputValue('');
                    }
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