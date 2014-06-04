/** @jsx React.DOM */

var React = require('react/addons');
var $ = window.jQuery = require('jquery');

require('./jquery.velocity.min');
require('./velocity.ui');

var Button = React.createClass({
  showForm: function() {
    this.props.form.show(this.props.options);
  },
  render: function() {
    return (
      <button
        className="payload-button"
        onClick={this.showForm}
        >
        Buy
      </button>
    );
  }
});

var Form = React.createClass({
  getInitialState: function() {
    return {
      options: {},
      hidden: true
    };
  },
  show: function(options) {
    this.setState({
      options: options,
      hidden: false
    });
    $(this.refs.overlay.getDOMNode())
      .velocity('fadeIn', 200);
    $(this.refs.box.getDOMNode())
      .velocity('transition.expandIn', 500);
    $(this.getDOMNode()).find('p')
      .velocity('transition.slideUpBigIn', {
        stagger: 100,
        duration: 500
      });
  },
  hide: function() {
    this.setState({hidden: true});
  },
  render: function() {
    var className = React.addons.classSet({
      'payload-form': true,
      'hidden': this.state.hidden
    });
    var options = this.state.options;
    return (
      <div className={className}>
        <div
          ref="overlay"
          className="overlay"
          onClick={this.hide}
        />
        <div
          ref="box"
          className="box"
          >
          <h2>{options.header}</h2>
          <p className="details">
            {options.desc} <span className="amount">({options.amount})</span>
          </p>
          <p>
            <input ref="number" type="text" placeholder="Cellphone #" />
          </p>
          <p>
            <button
              >
              Pay with Globe Load
            </button>
          </p>
          <p className="powered-by">
            Powered by PHonePay
          </p>
        </div>
      </div>
    );
  }
});


var container = document.createElement('div');
document.body.appendChild(container);

var form = React.renderComponent(
  <Form />,
  container
);

Array.prototype.forEach.call(
  document.querySelectorAll('.payload'),
  function(el) {
    React.renderComponent(
      <Button
        form={form}
        options={el.dataset}
      />,
      el
    );
  }
);

