import React, {useState} from 'react'
import ControlledInput from "./ControlledInput";
import SearchSimilarNewsButton from "./SearchSimilarNewsButton";
import axios from "axios";
import appConfig from 'configs/app.config'
import {useSelector} from "react-redux";
import {useNavigate} from "react-router-dom";
import dateToString from "../../utils/dateToString";
import {ScrollBar} from "../../components/ui";

const {apiPrefix} = appConfig


const SearchSimilarNews = () => {

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
        let req = new Request(newsApiUrl);

        fetch(req)
            .then(response => response.json())
            .then(res => {
                // console.log("Got from News API: ");

                if (res.status === "ok") {
                    // console.log(res.articles);
                    // console.log(res.status);
                    // console.log(res.totalResults);

                    axios.post(
                        `${apiPrefix}/add-query-history`,
                        {uid, url: inputValue, similarArticles: res.articles}
                    ).then(response => {
                        setLoading(false);
                        setInputDisabled(false);
                        setInputValue('');

                        navigate("/search-menu-query-history");
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
            <SearchSimilarNewsButton
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

export default SearchSimilarNews